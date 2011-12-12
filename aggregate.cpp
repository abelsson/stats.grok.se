/*
 * Copyright (C) 2011 Henrik Abelsson <henrik@grok.se>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#include <vector>
#include <iostream>
#include <fstream>
#include <string>
#include <cassert>
#include <sstream>
#include <algorithm>
#include <queue>
#include <iterator>
#include <cstring>
#include "qunit.h"

/**
 * A buffer in which lines can be peeked or consumed.
 */
class LinePeekableFile
{
        static const int CHUNK_SIZE = 10;
        
    public:
        LinePeekableFile(std::string name,std::istream *in):
            m_in(in),m_name(name),m_cachePresent(false),m_isGood(true)
        {
        }
        
        LinePeekableFile(const LinePeekableFile &other):
            m_in(other.m_in),m_cache(other.m_cache),m_name(other.m_name),
            m_cachePresent(other.m_cachePresent),m_isGood(other.m_isGood)
        {
        }
        
        LinePeekableFile &operator=(const LinePeekableFile &other)
        {
            if (this != &other)
            {
                m_isGood = other.m_isGood;
                m_cachePresent = other.m_cachePresent;
                m_cache = other.m_cache;
                m_name = other.m_name;
                m_in = other.m_in;
            }

            return *this;
        }
        
        const std::string &peek()
        {
            if(m_cachePresent)
            {
                return m_cache;
            }           
            getline(*m_in,m_cache);

            if (m_in->eof())
            {
                m_isGood = false;
            }
            m_cachePresent = true;
            return m_cache;
        }
        
        const std::string &get()
        {
            const std::string &ret = peek();
            m_cachePresent = false;
            return ret;
        }
        
        bool good()
        {
            return m_isGood;
        }

        const std::string &name()
        {
            return m_name;
        }
        
    private:
        std::istream *m_in;
        std::string m_cache;
        std::string m_name;
        
        bool m_cachePresent;
        bool m_isGood;
};


void tokenize(const std::string& str,
              std::vector<std::string>& tokens,
              const std::string& delimiters = " ")
{
    // Skip delimiters at beginning.
    std::string::size_type lastPos = str.find_first_not_of(delimiters, 0);
    // Find first "non-delimiter".
    std::string::size_type pos     = str.find_first_of(delimiters, lastPos);

    while (std::string::npos != pos || std::string::npos != lastPos)
    {
        // Found a token, add it to the vector.
        tokens.push_back(str.substr(lastPos, pos - lastPos));
        // Skip delimiters.  Note the "not_of"
        lastPos = str.find_first_not_of(delimiters, pos);
        // Find next "non-delimiter"
        pos = str.find_first_of(delimiters, lastPos);
    }
}



std::string urldecode(const std::string &in)
{
  std::string result;

  //std::cout  << "'" << in << "'" << std::endl;
  
  for(int i=0;i<in.length();i++)
  {
    if (in[i] == '%')
    {
      char ch[3];
      // Malformed, just ignore last.
      if (i > in.length() - 2)
          return result;
      ch[0]=in[++i]; ch[1] = in[++i]; ch[2]=0;
      unsigned char d = strtol(ch,0,16);
      result += d;
    }
    else
      result += in[i];
  }

  return result;
}

std::string trim(const std::string &in)
{
  if (in.empty())
    return "";
  
  int sidx=in.find_first_not_of(" \t\n");
  int eidx=in.find_last_not_of(" \t\n");

  if (sidx==std::string::npos || eidx==std::string::npos) 
    return "";
  
  return in.substr(sidx,eidx-sidx+1);
}

int getIndexOffset(std::string in)
{   
    char s[8];
    memset(s,0,8);
    strncpy(s,in.c_str(),7);
    
    long res = ((long)s[0])*(1ULL<<18)+s[1]*(1<<15)+s[2]*(1<<12)+s[3]*(1<<9)+s[4]*(1<<6)+s[5]*(1<<3)+s[6];
    return res;
}
void aggregate(std::vector<LinePeekableFile> &files,std::ostream &output)
{

    long long offset = 0;
    std::priority_queue<std::string,std::vector<std::string>,std::greater<std::string> > candidates;

    for(std::vector<LinePeekableFile>::iterator it = ++files.begin();
        it != files.end();
        it++)
    {
        const std::string candidate = it->peek();
        if (candidate != "")
        {
            
            int pos = candidate.find(' ',candidate.find(' ')+1); // find second ' '.
             
            candidates.push(candidate.substr(0,pos+1));
        }
    }
      
    while(!candidates.empty())
    {

        std::string curMin = candidates.top();
        candidates.pop();
        
        while (candidates.top() == curMin && !candidates.empty())
            candidates.pop();
        
        if (curMin == "")
            return;        

        int pos = curMin.length();
        
        
        std::vector<std::vector<LinePeekableFile>::iterator> toRemove;

        //std::cout <<  " curMin=" << curMin  << std::endl;
        //std::cout << "candidate size: " << candidates.size() << std::endl;
        //std::copy (candidates.begin(), candidates.end(), std::ostream_iterator<int>(std::cout, "\n"));
        
        std::stringstream line;

        std::string outline = curMin;
        outline[outline.find_first_of(' ')]='\t';
        
        line << urldecode(trim(outline)) << '\t';

        long cnt = 0;
        
        for(std::vector<LinePeekableFile>::iterator it = files.begin();
            it != files.end();
            it++)
	{
            
            if (it->peek().find(curMin) == 0)
	    {
                //std::cout << it->peek() << " == " <<  curMin << std::endl;
                std::string str = it->get();
                std::vector<std::string> tokens;
                tokenize(str,tokens);

                cnt += atoi(tokens[tokens.size()-2].c_str());
                //line << " " <<  ;


                str = it->peek();

                if (str != "")
                {
                   
                    int pos = str.find(' ',str.find(' ')+1); // find second ' '.
                    //std::cout << "pushing :" << str.substr(0,pos) << std::endl;
                    candidates.push(str.substr(0,pos+1));
                }
                
                if (!it->good())
                    toRemove.push_back(it);                
	    }
           
	}
        line << cnt << std::endl;

        offset += line.str().length();
        
        output << line.str();
        
        for(std::vector<std::vector<LinePeekableFile>::iterator>::iterator it = toRemove.begin();
            it != toRemove.end();
            it++)
	{
            files.erase(*it);
        }
    }
}

#ifdef TESTING

QUnit::UnitTest qunit(std::cerr, QUnit::normal);

void testLinePeek(std::string str)
{
    std::stringstream ibuf(str);
    LinePeekableFile lp("",&ibuf);
  
    QUNIT_IS_EQUAL(lp.peek(),"foo");
    QUNIT_IS_EQUAL(lp.get(),"foo");
    QUNIT_IS_EQUAL(lp.peek(),"bar");
    QUNIT_IS_EQUAL(lp.peek(),"bar");
  
    QUNIT_IS_EQUAL(lp.get(),"bar");
    QUNIT_IS_EQUAL(lp.get(),"bla");
    QUNIT_IS_EQUAL(lp.good(),true);
    QUNIT_IS_EQUAL(lp.get(),"baz");
    QUNIT_IS_EQUAL(lp.get(),"");
    QUNIT_IS_EQUAL(lp.good(),false);

}

void testAggregate()
{
    std::stringstream a("aa foo 1 1\n");
    std::stringstream b("aa foo 16 16\nbb foo 2 2\ncc nisse 3 3\n");
    std::stringstream c("aa bar 4 4\n");
    std::stringstream d("bb foo 8 8\n");
    
    std::vector<LinePeekableFile> files;
    files.push_back(LinePeekableFile("",&a));
    files.push_back(LinePeekableFile("",&b));
    files.push_back(LinePeekableFile("",&c));
    files.push_back(LinePeekableFile("",&d));

    std::stringstream output;
    aggregate(files,output);

    std::cout << output.str() << std::endl;

    std::string tmp;
    getline(output,tmp);
    QUNIT_IS_EQUAL(tmp,"aa bar 4");    
    getline(output,tmp);
    QUNIT_IS_EQUAL(tmp,"aa foo 17");
    getline(output,tmp);
    QUNIT_IS_EQUAL(tmp,"bb foo 10");

}
#endif

void test()
{
#ifdef TESTING    
    testLinePeek("foo\nbar\nbla\nbaz\n");
    testLinePeek("foo\nbar\nbla\nbaz");
    testAggregate();
#endif
}

int main(int argc,char *argv[])
{
    if (argc == 1)
    {
        test();
        return 0;
    }
    
    std::vector<LinePeekableFile> files;
    for(int i=1;i<argc;i++)
    {

        std::ifstream *inf = new std::ifstream(argv[i]);

        if (!inf)
        {
            std::cerr << "Couldn't open "  << argv[i] << std::endl;
            return -1;
        }
        
        files.push_back(LinePeekableFile(argv[i],inf));
    }
    aggregate(files,std::cout);
    
    return 0;
}
